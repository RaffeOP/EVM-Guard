pragma solidity 0.8.20;

contract Escrow5912 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(balances[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        balances[msg.sender] -= amount;
        reserve -= amount;
        locked = false;
    }

    function ownerOf_() public view returns (address) { return owner; }
}
