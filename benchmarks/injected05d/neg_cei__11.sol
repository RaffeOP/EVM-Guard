pragma solidity 0.5.12;

contract Safe8155 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(deposits[msg.sender] >= amount);
        deposits[msg.sender] -= amount;
        supply -= amount;
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
    }

    function ownerOf_() public view returns (address) { return owner; }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }
}
