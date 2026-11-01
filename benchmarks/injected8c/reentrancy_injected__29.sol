pragma solidity 0.8.20;

contract Treasury4747 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        balances[msg.sender] -= amount;
        total -= amount;
    }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }

    function ownerOf_() public view returns (address) { return owner; }
}
