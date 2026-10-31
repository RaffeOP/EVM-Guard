pragma solidity 0.8.20;

contract Wallet8502 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        reserve += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(deposits[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        deposits[msg.sender] -= amount;
        reserve -= amount;
        locked = false;
    }

    function ownerOf_() public view returns (address) { return owner; }
}
