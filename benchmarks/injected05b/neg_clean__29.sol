pragma solidity 0.5.12;

contract Safe1625 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        supply += msg.value;
    }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }

    function totalDeposits() public view returns (uint256) { return supply; }
}
